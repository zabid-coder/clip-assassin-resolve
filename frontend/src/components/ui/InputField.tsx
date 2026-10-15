import React, { useState } from 'react';
import { FolderSearch, FileSearch, Save } from 'lucide-react';
import { INPUT_STYLES } from './design-tokens';
import type { CategoryKey } from './design-tokens';

interface InputFieldProps {
  id: string;
  placeholder: string;
  defaultValue?: string;
  type?: string;
  className?: string;
  browseType?: 'folder' | 'file' | 'save';
  category?: CategoryKey; // Token system category
}

export const InputField: React.FC<InputFieldProps> = ({ id, placeholder, defaultValue = "", type = "text", className = "", browseType, category = 'neutral' }) => {
  const [loading, setLoading] = useState(false);

  const handleBrowse = async () => {
    setLoading(true);
    try {
      const API_BASE = import.meta.env.DEV ? "http://localhost:8000/api" : "/api";
      const res = await fetch(`${API_BASE}/browse?type=${browseType}`);
      const data = await res.json();
      
      if (data.success && data.path) {
        const inputEl = document.getElementById(id) as HTMLInputElement;
        if (inputEl) {
          inputEl.value = data.path;
          localStorage.setItem(`clipAssassin:${id}`,  data.path);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const ringStyle = INPUT_STYLES.focusRing(category);

  return (
    <div className="form-field">
      <label htmlFor={id} className="block text-xs text-white/60 mb-2">{placeholder}</label>
      <div className={`field-control ${browseType?'with-browse':''}`}>
      <input 
        id={id}
        aria-label={placeholder}
        type={type} 
        placeholder={placeholder}
        defaultValue={localStorage.getItem(`clipAssassin:${id}`) || defaultValue}
        onChange={(e) => localStorage.setItem(`clipAssassin:${id}`,  e.target.value)}
        className={`${INPUT_STYLES.base} ${browseType ? 'browse-value' : ''} ${className}`}
        style={ringStyle}
      />
      {browseType && (
        <button
          type="button"
          onClick={handleBrowse}
          disabled={loading}
          aria-label={`Browse for ${browseType}`}
          className={`field-browse ${loading?'is-loading':''}`}
          title={`Browse for ${browseType}`}
        >
          {browseType === 'folder' ? <FolderSearch size={16} /> : 
           browseType === 'file' ? <FileSearch size={16} /> : 
           <Save size={16} />}
        </button>
      )}
      </div>
    </div>
  );
};
