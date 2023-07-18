import { adminDb } from "@/firebaseAdmin";
import query from "@/lib/queryApi";
import admin from "firebase-admin"
import type { NextApiRequest, NextApiResponse } from "next";

type Data = {
    answer: string
}

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse<Data>,
){
    const { prompt, chatId, model, session } = req.body; 
    
    if(!prompt){
        res.status(400).json({ answer: "Please provide prompt" })
        return;
    }

    if(!chatId){
        res.status(400).json({ answer: "Please provide Chat ID" })
        return;
    }
    
    const response = await query(prompt, chatId, model)

    const message: Message = {
        text: response || "Sybil could not find the answer for that",
        createdAt: admin.firestore.Timestamp.now(),
        user: {
            _id:'polka-4b03b',
            name: 'polka',
            avatar: "https://links.papareact.com/89k",
        },
    };
    
    await adminDb
    .collection('users')
    .doc(session?.user?.email)
    .collection('chats')
    .doc(chatId)
    .collection('messages')
    .add(message)



    res.status(200).json({ answer:message.text })
}
    
