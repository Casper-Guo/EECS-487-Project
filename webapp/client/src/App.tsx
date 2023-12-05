import React, { useState, useEffect } from "react";
import { LoginModal } from "./components/LoginModal";
import { Navbar } from './components/Navbar';
import { Deck } from './components/Deck';

import './index.css';

const App: React.FC = () => {
	// Leave for debug
	/*
		const [apiEndpoints, setEndpoints] = useState<object>();
		useEffect(() => {
			fetch('/api/v1/')
			.then((response) => response.json())
			.then((endpoints) => setEndpoints(endpoints))
			.catch((err) => {
				console.log(err.message);
			});
		}, []);

		// Temporary to test api requests on front-end
		if (apiEndpoints) {
			console.log(apiEndpoints);
		}
	*/
	const [showLogin, setShowLogin] = useState(true);
	const updateShowLogin = (showLogin: boolean) => {
		setShowLogin(showLogin);
	}

	useEffect(() => {
		const state = JSON.parse(sessionStorage.getItem('login')!);
		if (state) {
			setShowLogin(state.showLogin);
		}
	}, []);
	useEffect(() => {
		sessionStorage.setItem('login', JSON.stringify({
			showLogin: showLogin
		}));
	});

    return (
		<div className="font-varela-round font-bold text-white">
			<Navbar />

			<main className="flex flex-col h-[calc(100vh-150px)] lg:h-[calc(100vh-75px)] items-center justify-center overflow-hidden">
                <Deck loggedIn={!showLogin}/>
			</main>

			{showLogin &&
				<LoginModal updateShowLogin={updateShowLogin}/>
			}
		</div>
	);
}

export default App;