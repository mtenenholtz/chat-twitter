function TextOutput(props) {
    return (
        props.value ? (
            <div className="py-4 px-2 border-2 bg-white border-black rounded-md outline-none h-full w-full text-black">
                {props.value}
            </div>
        ) : null
    );
  }
  
  export default TextOutput;