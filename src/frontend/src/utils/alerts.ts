export const showAlert = (message: string) => {
  if (import.meta.env.VITE_ENABLE_ALERTS === 'true') {
    alert(message);
  } else {
    console.log("Alert suppressed:", message);
  }
};
