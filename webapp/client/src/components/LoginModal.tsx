import React, { useState } from "react";

interface Props {
    updateShowLogin: (showLogin: boolean) => void;
}

export const LoginModal: React.FC<Props> = ({updateShowLogin}) => {
    const [user, setUser] = useState({
		username: ''
	});

	const { username } = user;

	const updateUser = (update: any) => {
		setUser({
			...user,
			[update.target.name]: update.target.value
		});
	}

	const [clickedLogin, setClickedLogin] = useState(false);

	const submitLogin = (form: any) => {
		setClickedLogin(true);
		fetch('/api/v1/login/', {
			method: 'POST',
			headers:{
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				username: username
			})
		})
		.then((response) => {
			if (response.status === 200) {
                updateShowLogin(false);
            }
		})
		.catch((error) => {
			console.log(error)
		});
	}

    return (
		<div className="fixed top-0 left-0 w-full h-full bg-gray-900 bg-opacity-75 flex justify-center items-center">
			<style>
				{`input[type=submit] {
					font-size: 1.25rem/* 20px */;
					line-height: 1.75rem/* 28px */;
				}`}
			</style>
			<div className="flex flex-col justify-center w-1/6 h-1/6 bg-violet-900 rounded-lg shadow-lg p-8">
				<label htmlFor="email" className="py-1 text-xl">Username</label>
				<input type="username" placeholder="username" autoComplete="off" name="username" value={username} onChange={updateUser} className="p-1 rounded-lg bg-violet-100 outline outline-1 outline-violet-500 text-black placeholder:text-gray-500" required />
				<br />
				<input type="submit" value="Login" onClick={submitLogin} className={clickedLogin ? "w-full h-1/5 shadow-xl rounded-lg bg-violet-500 hover:bg-violet-600 active:bg-violet-700 transition-all duration-300 cursor-progress" : "w-full h-1/5 shadow-xl rounded-lg bg-violet-500 hover:bg-violet-600 active:bg-violet-700 transition-all duration-300 cursosr-pointer"}/>
			</div>
		</div>
    );
}