import { initializeApp } from 'firebase/app'
import { getAnalytics, isSupported } from 'firebase/analytics'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

const firebaseConfig = {
  apiKey: 'AIzaSyAAM-WhAlJShdrj22p3RHod8QQ5EOGFI3o',
  authDomain: 'my-agent-a80b7.firebaseapp.com',
  databaseURL: 'https://my-agent-a80b7-default-rtdb.asia-southeast1.firebasedatabase.app',
  projectId: 'my-agent-a80b7',
  storageBucket: 'my-agent-a80b7.firebasestorage.app',
  messagingSenderId: '257152046508',
  appId: '1:257152046508:web:6447ceaf46017e28291609',
  measurementId: 'G-52DSXVBEJ2',
}

export const firebaseApp = initializeApp(firebaseConfig)
export const db = getFirestore(firebaseApp)
export const storage = getStorage(firebaseApp)
export const analyticsPromise = isSupported().then((supported) => (
  supported ? getAnalytics(firebaseApp) : null
))

export default firebaseApp
