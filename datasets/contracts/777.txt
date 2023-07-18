#![feature(ptr_const_cast)]

use env_logger;
use ffmpeg::{
    avcodec_get_class, avformat_alloc_context, avformat_alloc_output_context2,
    avformat_close_input, avformat_free_context, avformat_get_class, avformat_open_input,
	 avio_close, av_demuxer_iterate, av_muxer_iterate, AVOutputFormat,
    AVFormatContext, AVProbeData, AVFMT_FLAG_CUSTOM_IO, AVFMT_NOFILE, AVClassCategory, AVInputFormat,
};
use ffmpeg_sys_next as ffmpeg;
use log::debug;
use std::{
    ffi::{c_void, CStr, CString, NulError},
    fmt,
    path::Path,
    ptr::{self, drop_in_place, NonNull},
};
use thiserror::Error;

// TODO:
//
// - need to add test with libasan, memsan enabled in Cargo.toml
//   partially because we don't quite trust exposed Public ffmpeg API.
//
// Functions that need to be looked at
//
// - avformat_open_input
// - avformat_find_stream_info
// - avformat_alloc_output_contex2
// - avformat_new_stream
// - avcodec_find_encoder
// - avcodec_alloc_context3
// - avcodec_open2
// - avcodec_parameters_from_context
// - avcodec_parameters_copy
// - avformat_write_header
// - avcodec_send_frame
// - avcodec_receive_frame
// - av_packet_rescale_ts
// - av_interleaved_write_frame
// - av_buffersrc_add_frame_flags
// - av_buffersink_get_frame
// - av_write_trailer
//
//
// The entrypoint for input could be from
// - av_file_map
// - avformat_open_input
//
//
// NOTE: av_free doesn't age well :')
//
// https://sourcegraph.com/github.com/FFmpeg/FFmpeg@1a502b99e818ee7b8b2b56c4f5c27e31f674c555/-/blob/libavutil/mem.c?L246-262
//
// AVClass is an arbitary abstract inheritance model in ffmpeg
// Tree kind a structure since AVClass can embed itself.
//
// it has
// - class_name
// - function maps (based on name)
// - AVOption
// - AVClassCategory
//
// AVClassCategory
//
// enum of class list in ffmpegs
// this includes :
//
// - filter, encoder, decoder, muxer, demuxer, device((video)input, output), input, output, etc
//
// - https://sourcegraph.com/github.com/FFmpeg/FFmpeg@1a502b99e818ee7b8b2b56c4f5c27e31f674c555/-/blob/libavutil/log.h?L28-47
//
#[inline]
fn is_input_device(category: AVClassCategory) -> bool {
    category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_VIDEO_INPUT
        || category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_AUDIO_INPUT
        || category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_INPUT
}

#[inline]
fn is_output_device(category: AVClassCategory) -> bool {
    category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_VIDEO_OUTPUT
        || category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_AUDIO_OUTPUT
        || category == AVClassCategory::AV_CLASS_CATEGORY_DEVICE_OUTPUT
}

const ID3V2_HEADER_SIZE: usize = 10;
const ID3V2_DEFAULT_MAGIC: &'static [u8] = b"ID3";

//
// bytes size > 10 (it needs at least 10 bytes)
//
//
#[inline]
const fn ff_id3v2_eq<'a, 'b>(bytes: &'a [u8], magic: &'b [u8]) -> bool {
    // bytes size > 10 (it needs at least 10 bytes)
    //
    bytes.len() >= 10
        && bytes[0] == magic[0]
        && bytes[1] == magic[1]
        && bytes[2] == magic[2]
        && bytes[3] != 0xff
        && bytes[4] != 0xff
        && bytes[6] & 0x80 == 0
        && bytes[7] & 0x80 == 0
        && bytes[8] & 0x80 == 0
        && bytes[9] & 0x80 == 0
}

//
// int ff_id3v2_tag_len(const uint8_t *buf)
//
// NOTE: input `bytes`t should be bigger than 10 bytes
//
// https://sourcegraph.com/github.com/FFmpeg/FFmpeg@1a502b9/-/blob/libavformat/id3v2.c?L157-167
//
// int len = ((buf[6] & 0x7f) << 21) +
//           ((buf[7] & 0x7f) << 14) +
//           ((buf[8] & 0x7f) << 7) +
//           (buf[9] & 0x7f) +
//           ID3v2_HEADER_SIZE;
//
// if (buf[5] & 0x10)
//     len += ID3v2_HEADER_SIZE;
//
// NOTE: I honestly think ffmpeg impl ff_Id3v2_tag_len has a bug since
// u8 <= 8 bits, yet we shift left up to 21 & 14 bits.
//
//
// NOTE: we might need to re-implement this by
// https://id3.org/id3v2.3.0
//
#[inline]
const fn ff_id3v2_tag_len<'a>(bytes: &'a [u8]) -> usize {
    assert!(bytes.len() >= 10, "input should be bigger than 10 bytes");

    // error: this arithmetic operation will overflow
    //    --> src/lib.rs:124:26
    //     |
    // 124 |      let len = ((bytes[6] & 0x7f << 21) as usize
    //     |                             ^^^^^^^^^^ attempt to shift left by `21_i32`, which would overflow
    //     |
    //     = note: `#[deny(arithmetic_overflow)]` on by default
    //
    // error: this arithmetic operation will overflow
    //    --> src/lib.rs:125:20
    //     |
    // 125 |                     + (bytes[7] & 0x7f << 14) as usize
    //     |                                   ^^^^^^^^^^ attempt to shift left by `14_i32`, which would overflow
    //
    // let len = ((bytes[6] & 0x7f << 21) as usize
    // 				+ (bytes[7] & 0x7f << 14) as usize
    // 				+ (bytes[8] & 0x7f << 7) as usize
    // 				+ (bytes[9] & 0x7f) as usize
    // 				+ ID3V2_HEADER_SIZE) as usize;
    //
    let len =
        ((bytes[8] & 0x7f << 7) as usize + (bytes[9] & 0x7f) as usize + ID3V2_HEADER_SIZE) as usize;

    //
    if bytes[5] & 0x10 == 0x10 {
        len + ID3V2_HEADER_SIZE
    } else {
        len
    }
}

//
// This implementation of ffmpeg Registry is unsafe since ffmpeg implementation
// itself is kinda unsafe because of :
//
// - the iterator of the registry assumes that the array does have at least 1 element
//
// - it's probably unsafe to iterate while somebody remove something from
//   ffmpeg registry (whatever is it, muxers, demuxers, etc), since the index or
//   reference already being invalid and no mutex or what so ever.
//
// - the `indev_list_intptr` storing the first index in the array
//
// - it assume on `ill` defined contract of C that NULL always point to address `0`.
//
pub struct UnsafeRegistry {}

pub struct UnsafeMuxerIterator {
    inner: *mut c_void,
}

impl UnsafeMuxerIterator {
    // Initialize muxer iterator
    //
    // NOTE: av_*_iterate are based on `ill` assumption that
    // in C NULL always point to address `0`. Thus, we need to
    // initialize the `opaque` ptr into `null`.
    //
    const fn new() -> Self {
        UnsafeMuxerIterator {
            inner: ptr::null_mut(),
        }
    }
}

// NOTE: since we're using raw ptr we need to implement
//       our own Drop impl.
//
impl Drop for UnsafeMuxerIterator {
    fn drop(&mut self) {
        unsafe { ptr::drop_in_place(self.inner) }
    }
}

impl Iterator for UnsafeMuxerIterator {
    type Item = NonNull<AVOutputFormat>;

    //
    // opaque default value = NULL or uninitialized.
    //
    // static atomic_uintptr_t outdev_list_intptr  = ATOMIC_VAR_INIT(0);
    //
    // hhttps://github.com/FFmpeg/FFmpeg/blob/master/libavformat/allformats.c#L545-L562
    //
    // const AVOutputFormat *av_muxer_iterate(void **opaque)
    // {
    //     static const uintptr_t size = sizeof(muxer_list)/sizeof(muxer_list[0]) - 1;
    //     uintptr_t i = (uintptr_t)*opaque;
    //     const AVOutputFormat *f = NULL;
    //     uintptr_t tmp;
    //
    //     if (i < size) {
    //         f = muxer_list[i];
    //     } else if (tmp = atomic_load_explicit(&outdev_list_intptr, memory_order_relaxed)) {
    //         const AVOutputFormat *const *outdev_list = (const AVOutputFormat *const *)tmp;
    //         f = outdev_list[i - size];
    //     }
    //
    //     if (f)
    //         *opaque = (void*)(i + 1);
    //     return f;
    // }
    //
    // Note: since *_list are static privately defined, we can't do anything about this behavior until
    // it's being fixed upstream or we fix it ourself in ffmpeg library or fork it.
    //
    fn next(&mut self) -> Option<Self::Item> {
        // TODO: need to check this (ptr -> mut ptr).
        let format = unsafe { av_muxer_iterate(&mut self.inner) };

        NonNull::new(format.as_mut())
    }
}

//
// NOTE: this is unsafe iterator since everybody at runtime could invalidate
// ptr in static array without blocking or invalidating the iterator.
//
// See [[UnsafeRegistry]].
//
pub struct UnsafeDemuxerIterator {
    inner: *mut c_void,
}

impl UnsafeDemuxerIterator {
    // Initialize demuxer iterator
    //
    // NOTE: av_*_iterate are based on `ill` assumption that
    // in C NULL always point to address `0`. Thus, we need to
    // initialize the `opaque` ptr into `null`.
    //
    const fn new() -> Self {
        UnsafeDemuxerIterator {
            inner: ptr::null_mut(),
        }
    }
}

// NOTE: since we're using raw ptr we need to implement
//       our own Drop impl.
//
impl Drop for UnsafeDemuxerIterator {
    fn drop(&mut self) {
        unsafe { ptr::drop_in_place(self.inner) }
    }
}

impl Iterator for UnsafeDemuxerIterator {
    type Item = NonNull<AVInputFormat>;

    //
    // opaque default value = NULL or uninitialized.
    //
    // static atomic_uintptr_t indev_list_intptr  = ATOMIC_VAR_INIT(0);
    //
    // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/allformats.c#L564-L581
    //
    // const AVInputFormat *av_demuxer_iterate(void **opaque)
    // {
    //     NOTE: this is so dangerous, this only valid since demuxer_list won't be empty
    //     since it's being initialized statically.
    //
    //     if demuxer_list is empty this will cause segmentation faults, since demuxer_list
    //     don't have a value in index 0.
    //
    //     static const uintptr_t size = sizeof(demuxer_list)/sizeof(demuxer_list[0]) - 1;
    //     uintptr_t i = (uintptr_t)*opaque;
    //     const AVInputFormat *f = NULL;
    //     uintptr_t tmp;
    //
    //     if (i < size) {
    //         f = demuxer_list[i];
    //     } else if (tmp = atomic_load_explicit(&indev_list_intptr, memory_order_relaxed)) {
    //         const AVInputFormat *const *indev_list = (const AVInputFormat *const *)tmp;
    //         f = indev_list[i - size];
    //     }
    //
    //     if (f)
    //         *opaque = (void*)(i + 1);
    //     return f;
    // }
    //
    // Note: since *_list are static privately defined, we can't do anything about this behavior until
    // it's being fixed upstream or we fix it ourself in ffmpeg library or fork it.
    //
    fn next(&mut self) -> Option<Self::Item> {
        // TODO: need to check this (ptr -> mut ptr).
        let format = unsafe { av_demuxer_iterate(&mut self.inner) };

        NonNull::new(format.as_mut())
    }
}

impl UnsafeRegistry {
    //
    // list all demuxers by using iterator
    //
    pub fn demuxers() -> impl Iterator<Item = NonNull<AVInputFormat>> {
        UnsafeDemuxerIterator::new()
    }

    //
    // list all muxers by using iterator
    //
    pub fn muxers() -> impl Iterator<Item = NonNull<AVOutputFormat>> {
        UnsafeMuxerIterator::new()
    }
}

#[cfg(test)]
mod test_unsafe_registries {

    use super::UnsafeRegistry;

    #[test]
    fn test_registry_list_demuxers() {
        let mut demuxer_counter = 0;

        for _ in UnsafeRegistry::demuxers() {
            // since it's nonnull then we don't need to check whether ptr is correct or not
            demuxer_counter += 1;
        }

        assert_ne!(demuxer_counter, 0, "demuxer should be available");
    }

    #[test]
    fn test_registry_list_muxers() {
        let mut muxer_counter = 0;

        for _ in UnsafeRegistry::muxers() {
            // since it's nonnull then we don't need to check whether ptr is correct or not
            muxer_counter += 1;
        }

        assert_ne!(muxer_counter, 0, "muxer should be available");
    }
}

// av_probe_input_buffer2
//
// const AVInputFormat *av_probe_input_format3(const AVProbeData *pd, int is_opened, int *score_ret)
//
// need to be re-implemented in Rust
// av_probe_input_buffer2 -> av_probe_input_format2 -> av_probe_input_format3
//
// av_probe_input_format2 -> av_probe_input_format3
// https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/format.c#L206-L217
//
// - it probe for id3v2 tag
// - iterate for demuxer
//   - check for each demux by calling
//     - if it does have demux->read_probe,
//       - then got a score
//       - match the extensions for the demuxer
//       - check for ID3tag
//     - if check onlt for extensions
//     - match mime name
//
// tldr,
// - based on scoring probing input format
// - demux->read_probe
//
fn probe_input_format<'a>(bytes: &'a [u8], max: u64) {
    //
    //
    // if (lpd.buf_size > 10 && ff_id3v2_match(lpd.buf, ID3v2_DEFAULT_MAGIC)) {
    //     int id3len = ff_id3v2_tag_len(lpd.buf);
    //     if (lpd.buf_size > id3len + 16) {
    //         if (lpd.buf_size < 2LL*id3len + 16)
    //             nodat = ID3_ALMOST_GREATER_PROBE;
    //         lpd.buf      += id3len;
    //         lpd.buf_size -= id3len;
    //     } else if (id3len >= PROBE_BUF_MAX) {
    //         nodat = ID3_GREATER_MAX_PROBE;
    //     } else
    //         nodat = ID3_GREATER_PROBE;
    // }
    if ff_id3v2_eq(&bytes[0..10], ID3V2_DEFAULT_MAGIC) {
        // tag length
        let tag_len = ff_id3v2_tag_len(&bytes[0..10]);
    }
}

#[derive(Debug, Error)]
pub enum FormatError {
    #[error("unknown error")]
    UnknownError,

    // This error happens if :
    // - av_class doesn't exists in AVFormatContext
    // - ...
    //
    #[error("invalid class error")]
    InvalidClassError,

    //
    // This error happens if :
    // - path are invalid cstring when setting AVFormatContext.url
    //
    #[error("invalid path : `{0}`")]
    InvalidPathError(#[from] NulError),
}

//
// FormatContext
//
pub struct FormatContext {
    //
    // We store AVFormatContext ptr as NonNull ptr thus droping this struct
    // will also invalidate invariant of NonNull ptr, however, along of it's lifetime (until it's dropped)
    // this variance (no set to null for self.inner ptr) will *always* holds true.
    //
    inner: NonNull<AVFormatContext>,
}

//
// `avformat_open_input`
//
// We split avformat_open_input into several functions that implement specific behavior
// of avformat_open_input. By far from skimming only, avformat_open_input can be splitted
// into :
//
// - local file only (anything being inferred), you actually want everything to be inferred
//   rather than need to specify even for local files
//
// - remote file or custom I/O like URLs or some I/O that need to be demuxed (ex: RTMP urls).
//   With this type, you want to carefully buffer the streams (being handled by ffmpeg library).
//   Then, put some additional informations such as AVDictionary or AVInputFormat.
//
impl FormatContext {
    //
    // avformat_open_input are completely unsafe thus we try to re-create what it does
    // in Rust.
    //
    // Open input format from local file. This function will implement some partial
    // use case of avformat_open_input but only for local file implementation. Thus,
    // it's actually the same as calling avformat_open_input in C with :
    //
    // ```
    // avformat_open_input(fctx, filename, NULL, NULL)
    // ```
    //
    // Thus :
    //   - AVInputFormat will be NULL
    //   - AVDictionary will also be NULL
    //   - AVFormatContext will be initialized with default values
    //
    // - avformat_alloc_context will be called once to initialize new AVFormatContext
    //
    // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/demux.c#L207-L209
    //
    pub fn open_local(path: String) -> Result<FormatContext, FormatError> {
        // allocate avformat in here
        // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/demux.c#L216-L217
        //
        // with this NonNull we could always guarantee that
        // fctx will always be nonnull
        //
        match NonNull::new(unsafe { avformat_alloc_context() }) {
            //
            // Note: any error while still in the scope of initializing need to drop AVFormatContext
            // manually since in C lands it's heap allocated.
            //
            Some(mut fctx) => {
                let fctx_ref = unsafe { fctx.as_ref() };
                let fctx_mut_ref = unsafe { fctx.as_mut() };

                // ffformatcontext is casting function from
                // AVFormatContext to FFFormatContext
                // maybe we could skip it :')
                // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/demux.c#L218

                //
                // Note: AVClass is required since it's being used as type information in runtime
                // to model AV* derivated runtime structs in libav
                //
                if fctx_ref.av_class.is_null() {
                    // drop avformat context if there is an error
                    unsafe { drop_in_place(fctx.as_ptr()) };

                    return Err(FormatError::InvalidClassError);
                }

                // Note: set pb flags (it seems related to I/O access)
                // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/demux.c#L229-L230
                //
                // if it's being initialized for now then it's not being defined yet, thus
                // it's should be AVFMT_FLAG_CUSTOM_IO
                //
                // if !fctx_ref.pb.is_null() {
                //     fctx.as_mut().flags |= AVFMT_FLAG_CUSTOM_IO
                // }
                //
                // since pb is always null in local file
                // then let's actually assign it directly to AVFMT_FLAG_CUSTOM_IO
                //
                fctx_mut_ref.flags |= AVFMT_FLAG_CUSTOM_IO;

                // Assign url from string path
                // https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/demux.c#L235-L239
                //
                if !path.is_empty() {
                    let cpath = CString::new(path)?;
                    fctx_mut_ref.url = cpath.into_raw();
                }

                // TODO: probe input format2 using the buffer
                // av_probe_input_format2

                Ok(FormatContext { inner: fctx })
            }
            _ => Err(FormatError::UnknownError),
        }
    }
}

impl Drop for FormatContext {
    //
    // Drop function for InputFormat, this trying to replicate
    // avformat_close_input
    //
    // This will invalidate :
    //
    // - self.inner (AVFormatContext)
    // - call read_close for AVFormatContext.iformat.read_close
    // - set self.inner.pb to null_mut
    // - call avformat_free_context for self.inner
    // - call avio_close for self.inner.pb
    //
    fn drop(&mut self) {
        //
        // fetch AVFormatContext as mutable
        //
        let mut this = unsafe { self.inner.as_mut() };

        //
        // this.pb will be set as null_mut ptr when it's not a file
        // or it's a custom I/O, however somehow ffmpeg still
        // closing the I/O using avio_close.
        //
        // We might able to simplify this scenario later on.
        //
        // NOTE: this already ref mut
        //
        let pb = this.pb;

        // it try to checks whether iformat is exists
        // as_ref() for ptr alread checks whether it's alread null or not
        //
        match unsafe { this.iformat.as_ref() } {
            // if iformat is not null
            Some(iformat) => {
                // fetch the name from iformat
                // TODO: check whether we have another way to
                // check CStr compare in Rust without converting into bytes
                let name = unsafe { CStr::from_ptr((*this.iformat).name) };

                // TODO: should I still need to check the value of `pb` ?
                //
                if name.to_bytes().eq(b"image2") && iformat.flags & AVFMT_NOFILE == AVFMT_NOFILE {
                    this.pb = std::ptr::null_mut();
                }

                // call close iformat if only if read_close is defined
                //
                // Note: the returned value might relates if there is an  I/O error happened
                // thus if returned value is important we need to change this into map
                // instead. but since it's in drop method so let say we're leaking memory
                // in here. FFmpeg seems also ignore this read_close returned value.
                //
                iformat.read_close.iter().for_each(|func| {
                    let val = unsafe { func(this) };
                    debug!("return from read close: {}", val);
                });
            }
            //
            // if it's null checks flags == AVFMT_FLAG_CUSTOM_IO
            // then reset the this.pb
            //
            // NOTE: we're missing the information related to
            // AVFormatContext.flags with AVFormatContext.pb
            // it seems that both are related.
            //
            // TODO: should I still need to check the value of `pb` ?
            //
            _ => {
                if this.flags & AVFMT_FLAG_CUSTOM_IO == AVFMT_FLAG_CUSTOM_IO {
                    this.pb = std::ptr::null_mut();
                }
            }
        }

        // Note: this is kind a weird situation where somehow free context need
        // to be done first before it's children resources
        //

        // free avformat_context
        unsafe { avformat_free_context(this) };

        // close the I/O
        unsafe { avio_close(pb) };
    }
}
