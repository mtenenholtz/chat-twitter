function TextInput(props) {
  return (
      <textarea
        className="py-2 px-2 w-full h-full border-2 border-black rounded-md outline-none text-black"
        type="text"
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
      />
  );
}

export default TextInput;