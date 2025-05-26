type ShowAlert = {
  show: boolean;
  type: string;
  message: string;
};

const Alert = ({showAlert}: {showAlert: ShowAlert}) => {
  return (
    <div
      className={`w-1/5 z-50 fixed top-20 left-1/2 transform -translate-x-1/2 p-4 rounded-lg text-white text-center shadow-lg transition-opacity duration-300 ease-in-out ${
        showAlert.show ? "opacity-100" : "opacity-0"
      } ${
        showAlert.type === "success"
          ? "bg-gradient-to-r from-indigo-400 to-indigo-500"
          : "bg-gradient-to-r from-red-400 to-red-500"
      } 
            shadow-xl border border-gray-200 animate-bounce`}
    >
      <p className="text-lg font-semibold">{showAlert.message}</p>
    </div>
  );
};

export default Alert;
