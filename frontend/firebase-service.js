// TalentMatch AI - Firebase Cloud Integration Service
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { 
    getFirestore, 
    collection, 
    addDoc, 
    getDocs, 
    query, 
    orderBy, 
    limit, 
    onSnapshot, 
    serverTimestamp,
    doc,
    setDoc,
    deleteDoc
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// Firebase Configuration provided by user
const firebaseConfig = {
  apiKey: "AIzaSyBYuRJ4qi0akXOuQPS1Ar76dEr2eR7aX6E",
  authDomain: "talentmatch-ai-ff4b3.firebaseapp.com",
  projectId: "talentmatch-ai-ff4b3",
  storageBucket: "talentmatch-ai-ff4b3.firebasestorage.app",
  messagingSenderId: "314538870415",
  appId: "1:314538870415:web:242ca769ca1e23dbf412fa"
};

let app = null;
let db = null;
let isFirebaseConnected = false;

// Initialize Firebase App & Firestore Database
function initFirebase() {
    try {
        app = initializeApp(firebaseConfig);
        db = getFirestore(app);
        isFirebaseConnected = true;
        console.log("🔥 Firebase initialized successfully for project:", firebaseConfig.projectId);
        updateFirebaseStatusUI(true, "Firebase Cloud Connected");
        
        // Listen for real-time changes in Firestore screenings collection
        setupRealtimeListener();
    } catch (error) {
        console.error("❌ Firebase initialization error:", error);
        isFirebaseConnected = false;
        updateFirebaseStatusUI(false, "Firebase: Offline Mode");
    }
}

function updateFirebaseStatusUI(connected, text) {
    const badgeText = document.getElementById("firebaseStatusText");
    const badgeDot = document.getElementById("firebaseStatusDot");
    if (badgeText) badgeText.textContent = text;
    if (badgeDot) {
        badgeDot.className = "status-dot " + (connected ? "orange" : "red");
    }
}

/**
 * Stores a complete recruitment screening session into Firebase Firestore.
 * @param {Object} screeningData - Object containing session_id, jd_title, company, mode, required_skills, total_candidates, rankings
 */
async function saveScreeningToFirebase(screeningData) {
    if (!isFirebaseConnected || !db) {
        console.warn("Firebase not connected. Skipping cloud save.");
        return null;
    }

    try {
        const sessionId = screeningData.session_id || `sess_${Date.now()}`;
        const payload = {
            session_id: sessionId,
            session_name: screeningData.session_name || "Recruitment Drive",
            company: screeningData.company || "Company",
            mode: screeningData.mode || "persistent",
            jd_title: screeningData.jd_title || "Job Position",
            required_skills: screeningData.required_skills || [],
            total_candidates: screeningData.total_candidates || (screeningData.rankings ? screeningData.rankings.length : 0),
            rankings: screeningData.rankings || [],
            created_at: new Date().toISOString(),
            server_timestamp: serverTimestamp()
        };

        const docRef = doc(db, "screenings", sessionId);
        await setDoc(docRef, payload, { merge: true });
        console.log("✅ Session saved to Firebase Firestore with ID:", sessionId);

        // Update candidate documents in Firestore
        if (screeningData.rankings && Array.isArray(screeningData.rankings)) {
            for (const cand of screeningData.rankings) {
                const candDocId = `cand_${cand.candidate_id || cand.candidate_name.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase()}`;
                await setDoc(doc(db, "candidates", candDocId), {
                    session_id: sessionId,
                    candidate_id: cand.candidate_id,
                    candidate_name: cand.candidate_name,
                    filename: cand.filename || "",
                    last_match_score: cand.overall_match_percentage,
                    last_jd: screeningData.jd_title,
                    matching_skills: cand.matching_skills || [],
                    missing_skills: cand.missing_skills || [],
                    rank: cand.rank,
                    updated_at: new Date().toISOString()
                }, { merge: true });
            }
        }

        return sessionId;
    } catch (error) {
        console.error("❌ Error saving screening to Firebase:", error);
        return null;
    }
}

/**
 * Retrieves the latest screening session from Firebase Firestore.
 */
async function getLatestScreeningFromFirebase() {
    if (!isFirebaseConnected || !db) return null;

    try {
        const q = query(collection(db, "screenings"), orderBy("created_at", "desc"), limit(1));
        const querySnapshot = await getDocs(q);
        
        if (!querySnapshot.empty) {
            const docSnap = querySnapshot.docs[0];
            const data = docSnap.data();
            data.id = docSnap.id;
            console.log("📥 Retrieved latest screening from Firebase:", data.jd_title);
            return data;
        }
        return null;
    } catch (error) {
        console.error("❌ Error fetching latest screening from Firebase:", error);
        return null;
    }
}

/**
 * Retrieves all stored screening sessions from Firebase Firestore.
 */
async function getAllScreeningsFromFirebase() {
    if (!isFirebaseConnected || !db) return [];

    try {
        const q = query(collection(db, "screenings"), orderBy("created_at", "desc"), limit(50));
        const querySnapshot = await getDocs(q);
        const list = [];
        querySnapshot.forEach(docSnap => {
            const data = docSnap.data();
            data.id = docSnap.id;
            list.push(data);
        });
        return list;
    } catch (error) {
        console.error("❌ Error fetching screening history from Firebase:", error);
        return [];
    }
}

/**
 * Deletes a single session from Firebase Firestore.
 */
async function deleteSessionFromFirebase(sessionId) {
    if (!isFirebaseConnected || !db || !sessionId) return false;
    try {
        await deleteDoc(doc(db, "screenings", sessionId));
        console.log("🗑️ Session deleted from Firebase:", sessionId);
        return true;
    } catch (error) {
        console.error("❌ Error deleting session from Firebase:", error);
        return false;
    }
}

/**
 * Deletes all screening session documents from Firebase Firestore.
 */
async function deleteAllSessionsFromFirebase() {
    if (!isFirebaseConnected || !db) return false;
    try {
        const querySnapshot = await getDocs(collection(db, "screenings"));
        const promises = [];
        querySnapshot.forEach(docSnap => {
            promises.push(deleteDoc(docSnap.ref));
        });
        await Promise.all(promises);
        console.log("🗑️ All screening sessions cleared from Firebase Firestore.");
        return true;
    } catch (error) {
        console.error("❌ Error clearing all sessions from Firebase:", error);
        return false;
    }
}

/**
 * Listens for real-time changes in the 'screenings' collection.
 */
function setupRealtimeListener() {
    if (!db) return;
    try {
        const q = query(collection(db, "screenings"), orderBy("created_at", "desc"), limit(1));
        onSnapshot(q, (snapshot) => {
            if (!snapshot.empty) {
                console.log("⚡ Real-time update received from Firebase Firestore!");
                const badgeText = document.getElementById("firebaseStatusText");
                if (badgeText) badgeText.textContent = "Firebase: Real-time Live";
            }
        }, (error) => {
            console.warn("Real-time listener notice:", error);
        });
    } catch (e) {
        console.warn("Real-time setup warning:", e);
    }
}

// Initialize on script load
initFirebase();

// Expose methods globally for app.js integration
window.FirebaseService = {
    isFirebaseConnected: () => isFirebaseConnected,
    saveScreeningToFirebase,
    getLatestScreeningFromFirebase,
    getAllScreeningsFromFirebase,
    deleteSessionFromFirebase,
    deleteAllSessionsFromFirebase
};
