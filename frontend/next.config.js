/** @type {import('next').NextConfig} */
const nextConfig = {
    images:{
       domains: ['imgur.com', 'i.imgur.com'],
    },
    reactStrictMode: true,
    experimental:{
        appDir: true,
    }
}

module.exports = nextConfig
