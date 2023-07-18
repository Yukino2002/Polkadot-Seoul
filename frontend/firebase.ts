// Import the functions you need from the SDKs you need
import { getApp, getApps, initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCs6yGo9DXzGpqLgVPpV_5FWOWPuSOPokw",
  authDomain: "polka-4b03b.firebaseapp.com",
  projectId: "polka-4b03b",
  storageBucket: "polka-4b03b.appspot.com",
  messagingSenderId: "459329796026",
  appId: "1:459329796026:web:37eae1a4eeab74e6b24f83"
};

// Initialize Firebase
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const db = getFirestore(app);

export { db };