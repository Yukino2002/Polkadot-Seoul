interface Message{
    text: string,
    createdAt: AppBuildManifest.firestore.Timestamp;
    user:{
        _id: string;
        name: string;
        avatar: string;
    }
}