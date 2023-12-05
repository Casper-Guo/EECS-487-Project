import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, cardData } from './Card';
import { InteractionBox } from './InteractionBox';
import { DoneModal } from './DoneModal';

interface Props {
	loggedIn: boolean;
}

export const Deck: React.FC<Props> = ({ loggedIn }) => {
	const [showDone, setDone] = useState(false);

	const [ card, setCard ] = useState<cardData>();
	const updateCard = () => {
		if (loggedIn) {
			fetch('/api/v1/cards/', {
				headers: {
					'Content-Type': 'application/json',
					'Accept': 'application/json'
				}
			})
			.then((response) => response.json())
			.then((data) =>  {
				if (data.done) {
					setDone(true);
					sessionStorage.setItem('done', JSON.stringify({done: true}));
				}
				else {
					setCard(data);
				}
			})
			.catch((err) => console.log(err));
		}
	}

	const [clicked_words, setClicked ] = useState<number[]>([]);
	const updateClicked = (index: number) => {
		let new_clicked = clicked_words;

		const idx = new_clicked?.indexOf(index);
		if (idx !== -1) {
			new_clicked?.splice(idx!, 1);
		}
		else {
			new_clicked?.push(index);
		}

		setClicked(new_clicked);

		sessionStorage.setItem('clicked_words', JSON.stringify({
			clicked_words: clicked_words
		}));
	}

	const [is_flipped, setFlip] = useState(false);
	const [time_flipped, setTimeFlipped] = useState<number>();
	const onFlip = (flip: boolean, time: number) => {
		setFlip(flip);
		setTimeFlipped(time);
	}

	const onNext = () => {
		const seen_card = {
			scores: clicked_words
		}

		console.log(clicked_words)

		fetch('/api/v1/cards/', {
			method: 'POST',
			mode: 'cors',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(seen_card)
		})
		.then(() => {
			sessionStorage.removeItem('clicked_words');
			updateCard();
			setFlip(false);
			setClicked([]);
			console.log(clicked_words)
		});
	}

	// initially load card
	useEffect(() => {
		updateCard();
	}, [loggedIn]);

	// to rehydrate state after refreshes
	useEffect(() => {
		let state = JSON.parse(sessionStorage.getItem('flips')!);
		if (state) {
			setFlip(state.is_flipped);
			setTimeFlipped(state.time_flipped);
		}

		state = JSON.parse(sessionStorage.getItem('clicked_words')!);
		if (state) {
			setClicked(state.clicked_words);
		}

		state = JSON.parse(sessionStorage.getItem('done')!);
		if (state){
			setDone(state.done);
		}

	}, []);
	useEffect(() => {
		sessionStorage.setItem('flips', JSON.stringify({
			is_flipped: is_flipped,
			time_flipped: time_flipped
		}));
	});

	if (!card) {
		return (
			<div className="flex w-10/12 h-4/6 items-center overflow-x-scroll rounded-lg shadow-2xl bg-violet-100">
				<div className="animate-pulse flex">
					<div className="flex items-center justify-center w-96 h-96 bg-gray-300 rounded-lg dark:bg-gray-700 m-24">
						<svg className="w-12 h-12 text-gray-200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" fill="currentColor" viewBox="0 0 640 512"><path d="M480 80C480 35.82 515.8 0 560 0C604.2 0 640 35.82 640 80C640 124.2 604.2 160 560 160C515.8 160 480 124.2 480 80zM0 456.1C0 445.6 2.964 435.3 8.551 426.4L225.3 81.01C231.9 70.42 243.5 64 256 64C268.5 64 280.1 70.42 286.8 81.01L412.7 281.7L460.9 202.7C464.1 196.1 472.2 192 480 192C487.8 192 495 196.1 499.1 202.7L631.1 419.1C636.9 428.6 640 439.7 640 450.9C640 484.6 612.6 512 578.9 512H55.91C25.03 512 .0006 486.1 .0006 456.1L0 456.1z"/></svg>
					</div>
				</div>
				<div className="w-full mr-24 animate-pulse">
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
						<div className="h-6 my-12 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
				</div>
			</div>
		);
	}

	return (
		<>
			{showDone &&
				<div>
					<DoneModal/>
				</div>
			}
			<motion.span animate={{ rotateY: !showDone && is_flipped && (Date.now() - time_flipped! < 1000) ? 360 : 0}} transition={{ ease: "easeInOut", duration: 0.75}} className="flex w-10/12 h-4/6 py-6">
				<Card card={card} is_flipped={is_flipped} clicked_words={clicked_words} updateClicked={updateClicked}/>
			</motion.span>
			{
				<InteractionBox onFlip={onFlip} is_flipped={is_flipped} onNext={onNext}/>
			}
		</>
	);
}
