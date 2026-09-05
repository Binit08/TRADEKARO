'use client'

import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import gsap from 'gsap'
import styles from '../login.module.css'

export interface AnimatedCharactersHandle {
  setFormFocus: (focused: boolean) => void;
  setTypingIntensity: (intensity: number) => void;
  playSuccessAnimation: () => void;
}

interface AnimatedCharactersProps {
  isPasswordVisible: boolean;
  passwordInputRef: React.RefObject<HTMLInputElement | null>;
}

export const AnimatedCharacters = forwardRef<AnimatedCharactersHandle, AnimatedCharactersProps>(
  ({ isPasswordVisible, passwordInputRef }, ref) => {
    // Refs for characters and elements
    const blueCharRef = useRef<HTMLDivElement>(null)
    const blackCharRef = useRef<HTMLDivElement>(null)
    const yellowCharRef = useRef<HTMLDivElement>(null)
    const orangeCharRef = useRef<HTMLDivElement>(null)
    const customCursorRef = useRef<HTMLDivElement>(null)
    
    const isPasswordVisibleRef = useRef(isPasswordVisible)
    const isIntroComplete = useRef(false)
    
    // Sync the prop to ref for the animation loop
    useEffect(() => {
      isPasswordVisibleRef.current = isPasswordVisible;
    }, [isPasswordVisible]);

    // Animation state refs
    const animState = useRef({
      isFocusedOnForm: false,
      currentTarget: { x: 0, y: 0 },
      mousePosition: { x: 0, y: 0 },
      rawMouse: { x: -100, y: -100 },
      typingIntensity: 0,
      time: 0,
      animationFrameId: 0
    })

    useImperativeHandle(ref, () => ({
      setFormFocus: (focused: boolean) => {
        animState.current.isFocusedOnForm = focused;
        if (focused && !isPasswordVisibleRef.current) {
            animState.current.mousePosition.x = window.innerWidth / 2 + 200;
            animState.current.mousePosition.y = window.innerHeight / 2;
        }
      },
      setTypingIntensity: (intensity: number) => {
        animState.current.typingIntensity = intensity;
      },
      playSuccessAnimation: () => {
        const chars = [blueCharRef.current, blackCharRef.current, yellowCharRef.current, orangeCharRef.current];
        chars.forEach(char => {
            if (char) {
               gsap.to(char, { y: -20, duration: 0.2, yoyo: true, repeat: 1, ease: "power2.out" });
            }
        });
      }
    }));

    useEffect(() => {
      animState.current.currentTarget = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
      animState.current.mousePosition = { x: window.innerWidth / 2, y: window.innerHeight / 2 };

      // Intro animation
      const tl = gsap.timeline({
        onComplete: () => {
          isIntroComplete.current = true;
        }
      });

      if (blueCharRef.current) {
        tl.fromTo(blueCharRef.current,
          { y: -250, opacity: 0, scaleY: 1.2, scaleX: 0.85 },
          { y: 0, opacity: 1, scaleY: 1, scaleX: 1, duration: 0.8, ease: "back.out(1.7)" }, 0
        );
      }
      if (blackCharRef.current) {
        tl.fromTo(blackCharRef.current,
          { y: 150, opacity: 0, scaleY: 0.6, scaleX: 1.2 },
          { y: 0, opacity: 1, scaleY: 1, scaleX: 1, duration: 0.8, ease: "back.out(1.5)" }, 0.1
        );
      }
      if (orangeCharRef.current) {
        tl.fromTo(orangeCharRef.current,
          { x: -120, opacity: 0, skewX: 20 },
          { x: 0, opacity: 1, skewX: 0, duration: 0.8, ease: "back.out(1.5)" }, 0.2
        );
      }
      if (yellowCharRef.current) {
        tl.fromTo(yellowCharRef.current,
          { x: 120, opacity: 0, skewX: -20 },
          { x: 0, opacity: 1, skewX: 0, duration: 0.8, ease: "back.out(1.5)" }, 0.25
        );
      }
      tl.fromTo(`.${styles.formContainer}`,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.0, ease: "power2.out" }, 0.4
      );

      // Mouse tracking
      const handleMouseMove = (e: MouseEvent) => {
        animState.current.rawMouse.x = e.clientX;
        animState.current.rawMouse.y = e.clientY;

        if (!animState.current.isFocusedOnForm) {
          animState.current.mousePosition.x = e.clientX;
          animState.current.mousePosition.y = e.clientY;
        }
      };
      
      document.addEventListener('mousemove', handleMouseMove);
      
      // Animation Loop
      const animate = () => {
        const state = animState.current;
        state.time += 0.15;
        state.typingIntensity *= 0.92;

        if (customCursorRef.current) {
          customCursorRef.current.style.left = `${state.rawMouse.x}px`;
          customCursorRef.current.style.top = `${state.rawMouse.y}px`;
        }

        let ease = 0.08;

        if (passwordInputRef.current && document.activeElement === passwordInputRef.current && !isPasswordVisibleRef.current) {
          const lookAwayTargetX = -window.innerWidth * 0.2;
          const lookAwayTargetY = -window.innerHeight * 0.2;
          state.mousePosition.x = lookAwayTargetX;
          state.mousePosition.y = lookAwayTargetY;
          ease = 0.03;
        }

        state.currentTarget.x += (state.mousePosition.x - state.currentTarget.x) * ease;
        state.currentTarget.y += (state.mousePosition.y - state.currentTarget.y) * ease;

        const updateEyes = (targetX: number, targetY: number) => {
            const chars = [
              { element: blueCharRef.current, hasWhiteEyes: true, maxMove: 5, hasBeak: false },
              { element: blackCharRef.current, hasWhiteEyes: true, maxMove: 4, hasBeak: false },
              { element: yellowCharRef.current, hasWhiteEyes: false, maxMove: 3, hasBeak: true },
              { element: orangeCharRef.current, hasWhiteEyes: false, maxMove: 3, hasBeak: false }
            ];

            chars.forEach(char => {
                if (!char.element) return;
                if (isPasswordVisibleRef.current) return;
                
                const eyes = char.element.querySelectorAll(`.${styles.eye}`);
                const pupils = char.element.querySelectorAll(`.${styles.pupil}`);
                
                eyes.forEach((eye: any, index: number) => {
                    const trackingElement = char.hasWhiteEyes ? eye : eye.parentElement;
                    if (!trackingElement) return;
                    
                    const trackRect = trackingElement.getBoundingClientRect();
                    const eyeCenterX = trackRect.left + trackRect.width / 2;
                    const eyeCenterY = trackRect.top + trackRect.height / 2;
        
                    const deltaX = targetX - eyeCenterX;
                    const deltaY = targetY - eyeCenterY;
                    const angle = Math.atan2(deltaY, deltaX);
                    const distance = Math.min(Math.sqrt(deltaX * deltaX + deltaY * deltaY) / 100, 1);
        
                    const moveX = Math.cos(angle) * char.maxMove * distance;
                    const moveY = Math.sin(angle) * char.maxMove * distance;
        
                    if (char.hasWhiteEyes && pupils && pupils[index]) {
                        (pupils[index] as HTMLElement).style.transform = `translate(${moveX}px, ${moveY}px)`;
                    } else if (!char.hasWhiteEyes) {
                        eye.style.transform = `translate(${moveX * 1.5}px, ${moveY * 1.5}px)`;
                    }
                });

                if (char.hasBeak) {
                    const beak = char.element.querySelector(`.${styles.beak}`) as HTMLElement;
                    if (beak) {
                        const trackRect = beak.getBoundingClientRect();
                        const centerX = trackRect.left + trackRect.width / 2;
                        const centerY = trackRect.top + trackRect.height / 2;
            
                        const deltaX = targetX - centerX;
                        const deltaY = targetY - centerY;
                        const angle = Math.atan2(deltaY, deltaX);
                        const distance = Math.min(Math.sqrt(deltaX * deltaX + deltaY * deltaY) / 100, 1);
            
                        const beakMove = char.maxMove * 1.8;
                        const moveX = Math.cos(angle) * beakMove * distance;
                        const moveY = Math.sin(angle) * beakMove * distance;
            
                        beak.style.transform = `translate(${moveX}px, ${moveY}px)`;
                    }
                }
            });
        };

        if (!isPasswordVisibleRef.current) {
          updateEyes(state.currentTarget.x, state.currentTarget.y);

          if (isIntroComplete.current) {
              const windowCenterX = window.innerWidth / 2;
              const windowHeight = window.innerHeight;

              const leanRatio = (state.currentTarget.x - windowCenterX) / (windowCenterX * 0.8);
              const clampedRatio = Math.max(-1, Math.min(1, leanRatio));

              let yRatio = Math.max(0, (state.currentTarget.y - windowHeight / 2) / (windowHeight / 2));
              if (passwordInputRef.current && document.activeElement === passwordInputRef.current) yRatio = 0;

              const squashFactor = 1 - (yRatio * 0.06);

              const grooveRot = Math.sin(state.time) * state.typingIntensity * 4;
              const grooveSquash = Math.abs(Math.sin(state.time * 2)) * state.typingIntensity * 0.05;

              [blueCharRef.current, blackCharRef.current, yellowCharRef.current, orangeCharRef.current].forEach(char => {
                  if (!char) return;
                  
                  let maxLean = 6;
                  if (char === blueCharRef.current) maxLean = 10;
                  if (char === orangeCharRef.current) maxLean = 3;

                  const totalRot = (clampedRatio * maxLean) + grooveRot;
                  const skew = totalRot * 0.6;
                  const totalScaleY = squashFactor - grooveSquash;

                  char.style.transform = `rotate(${totalRot * 0.3}deg) skewX(${skew}deg) scaleY(${totalScaleY})`;
              });
          }
        } else {
          if (isIntroComplete.current) {
              [blueCharRef.current, blackCharRef.current, yellowCharRef.current, orangeCharRef.current].forEach(char => {
                  if (char) char.style.transform = 'rotate(0deg) skewX(0deg) scaleY(1)';
              });
          }
        }

        state.animationFrameId = requestAnimationFrame(animate);
      };

      animState.current.animationFrameId = requestAnimationFrame(animate);

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        cancelAnimationFrame(animState.current.animationFrameId);
      };
    }, [passwordInputRef]); // added passwordInputRef to dependency array just in case

    return (
      <>
        <div className={styles.charactersSection}>
          <div className={styles.charactersWrapper}>
            <div ref={orangeCharRef} className={`${styles.character} ${styles.orangeSemicircle} ${isPasswordVisible ? styles.lookingAway : ''}`}>
              <div className={styles.face}>
                <div className={`${styles.eye} ${styles.leftEye}`}><div className={styles.pupil}></div></div>
                <div className={`${styles.eye} ${styles.rightEye}`}><div className={styles.pupil}></div></div>
                <div className={styles.mouth}></div>
              </div>
            </div>
            <div ref={blueCharRef} className={`${styles.character} ${styles.blueRectangle} ${isPasswordVisible ? styles.lookingAway : ''}`}>
              <div className={styles.face}>
                <div className={`${styles.eye} ${styles.leftEye}`}><div className={styles.pupil}></div></div>
                <div className={`${styles.eye} ${styles.rightEye}`}><div className={styles.pupil}></div></div>
              </div>
            </div>
            <div ref={blackCharRef} className={`${styles.character} ${styles.blackPenguin} ${isPasswordVisible ? styles.lookingAway : ''}`}>
              <div className={styles.face}>
                <div className={`${styles.eye} ${styles.leftEye}`}><div className={styles.pupil}></div></div>
                <div className={`${styles.eye} ${styles.rightEye}`}><div className={styles.pupil}></div></div>
              </div>
            </div>
            <div ref={yellowCharRef} className={`${styles.character} ${styles.yellowBird} ${isPasswordVisible ? styles.lookingAway : ''}`}>
              <div className={styles.beak}></div>
              <div className={styles.face}>
                <div className={`${styles.eye} ${styles.leftEye}`}><div className={styles.pupil}></div></div>
                <div className={`${styles.eye} ${styles.rightEye}`}><div className={styles.pupil}></div></div>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.customCursor} ref={customCursorRef}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 2L10.5 22L13.5 13.5L22 10.5L2 2Z" strokeWidth="1.5" strokeLinejoin="round" />
          </svg>
        </div>
      </>
    );
  }
);

AnimatedCharacters.displayName = 'AnimatedCharacters';
