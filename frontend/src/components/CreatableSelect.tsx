type Props = {
  label: string;
  value?: string;
  options: string[];
  onChange: (value: string) => void;
};

export function CreatableSelect({ label, value, options, onChange }: Props) {
  return (
    <label>
      {label}
      <input list={`${label}-options`} value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
      <datalist id={`${label}-options`}>
        {options.map((option) => (
          <option key={option} value={option} />
        ))}
      </datalist>
    </label>
  );
}
