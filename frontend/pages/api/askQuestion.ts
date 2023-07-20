import { adminDb } from "@/firebaseAdmin";
import query from "@/lib/queryApi";
import admin from "firebase-admin"
import cors from 'cors'
import { db } from "@/firebase";
import { setDoc, addDoc, doc, serverTimestamp } from "firebase/firestore";
import type { NextApiRequest, NextApiResponse } from "next";

type Data = {
    answer: string
}

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse<Data>,
) {
    const { prompt, chatId, session } = JSON.parse(req.body)

    const mnemonic = req.headers.mnemonic
    const openai = req.headers.openai

    if (!prompt) {
        res.status(400).json({ answer: "Please provide prompt" })
        return;
    }

    if (!chatId) {
        res.status(400).json({ answer: "Please provide Chat ID" })
        return;
    }

    const headers: any = {
        'Content-Type': 'application/json',
        Openaikey: openai,
        Mnemonic: mnemonic
    }

    const body = {
        prompt,
        chatId,
        user: session.user
    }

    const response = await fetch("http://localhost:8001/openai", {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    })

    const data = await response.json()
    console.log(data)

    const message = {
        text: data.response,
        createdAt: serverTimestamp(),
        user: session.user
    }

    // update firebase

    await setDoc(doc(db, 'users', session?.user?.email!, 'chats', chatId, 'messages', Math.random().toString(36).substring(7)), {
        message
    });

    // const message: Message = {
    //     text: response || "Sybil could not find the answer for that",
    //     createdAt: admin.firestore.Timestamp.now(),
    //     user: {
    //         _id: 'polka-4b03b',
    //         name: 'polka',
    //         avatar: "https://links.papareact.com/89k",
    //     },
    // };

    // await adminDb
    //     .collection('users')
    //     .doc(session?.user?.email)
    //     .collection('chats')
    //     .doc(chatId)
    //     .collection('messages')
    //     .add(message)



    // res.status(200).json({ answer: message.text })
    res.status(200).json({ answer: "Hello" })
}

