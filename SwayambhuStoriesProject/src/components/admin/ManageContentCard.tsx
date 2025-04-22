// src/components/admin/ManageContentCard.tsx
import React, { useState, ChangeEvent, FormEvent } from "react";

// Assuming API_URL is defined elsewhere or define it here
// const API_URL = "https://your-backend-url.com";
const API_URL = "http://localhost:5000"; // Make sure this matches your backend

// Define the structure of a search result item (matching your MongoDB schema)
interface ContentItem {
    _id: string; // MongoDB default ID
    job_id: string;
    title?: string | null;
    url?: string | null;
    source_location: string;
    source_type: 'youtube' | 'mp4';
    speaker?: string | null;
    location?: string | null;
    category?: string | null; // Renamed from 'type'
    keywords?: string[];
    detected_language?: string;
    date_added?: string;
    last_updated?: string;
    processing_info?: Record<string, any>; // Include processing info if needed
    // Add other relevant fields from your schema
}

// Define the fields available for searching
const searchFields = [
    { value: "title", label: "Title" },
    { value: "source_location", label: "Source (URL/Filename)" },
    { value: "keywords", label: "Keywords" },
    { value: "speaker", label: "Speaker" },
    { value: "job_id", label: "Job ID" },
    // Add more fields if needed e.g., category, location
];

// Define which fields are editable (using keys of ContentItem)
const editableFields: (keyof ContentItem)[] = [
    'title', 'url', 'speaker', 'location', 'category', 'keywords'
];

// Define the structure of the form data for editing
// This maps the editable fields from ContentItem to their representation in the form
type EditFormData = {
    [K in (typeof editableFields)[number]]: K extends 'keywords' ? string : string;
    // If you add non-string editable fields in the future, adjust the mapping here.
};

// The resulting type is { title?: string, url?: string, ..., keywords?: string }


const ManageContentCard: React.FC = () => {
    const [searchField, setSearchField] = useState<string>(searchFields[0].value); // Default to first field
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [searchResults, setSearchResults] = useState<ContentItem[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const [editingItemId, setEditingItemId] = useState<string | null>(null); // Use _id for editing
    // Use the new EditFormData type for the state holding form changes
    // FIX: Cast {} to EditFormData for initial state
    const [editFormData, setEditFormData] = useState<EditFormData>({} as EditFormData);

    // --- Search Handler ---
    const handleSearch = async (e?: FormEvent) => {
        if (e) e.preventDefault(); // Prevent page reload if called from form submit
        if (!searchQuery.trim()) {
            setError("Please enter a search query.");
            setSearchResults([]);
            return;
        }
        setLoading(true);
        setError(null);
        setSearchResults([]); // Clear previous results
        setEditingItemId(null); // Exit edit mode on new search

        try {
            // Construct query params carefully
            const params = new URLSearchParams({
                field: searchField,
                query: searchQuery.trim(),
            });
            const response = await fetch(`${API_URL}/api/search-content?${params.toString()}`);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(errorData.message || `Search failed with status: ${response.status}`);
            }

            const data: ContentItem[] = await response.json();
            setSearchResults(data);
            if (data.length === 0) {
                setError("No results found.");
            }

        } catch (err: any) {
            console.error("Search error:", err);
            setError(err.message || "An error occurred during search.");
            setSearchResults([]);
        } finally {
            setLoading(false);
        }
    };

    // --- Edit Mode Handlers ---
    const handleEditClick = (item: ContentItem) => {
        setEditingItemId(item._id);
        // Initialize form data with current item values, handle potential null/undefined
        // FIX: Cast {} to EditFormData for the initial data object
        const initialData: EditFormData = {} as EditFormData;
        editableFields.forEach(field => {
            if (field === 'keywords') {
                // Keywords in ContentItem is string[], in EditFormData is string
                initialData.keywords = (item.keywords || []).join(', ');
            } else {
                // For other editable fields, get the value from the item
                const itemValue = item[field];
                // Convert to string for the form data, default to empty string for null/undefined
                 if (itemValue !== undefined && itemValue !== null) {
                     // Assign directly to the field in initialData
                     initialData[field as keyof EditFormData] = String(itemValue);
                 } else {
                     initialData[field as keyof EditFormData] = ''; // Default to empty string
                 }
            }
        });
        setEditFormData(initialData);
        setError(null); // Clear any previous errors
    };

    const handleCancelEdit = () => {
        setEditingItemId(null);
        // Reset form data by setting it to an empty object cast to EditFormData
        // FIX: Cast {} to EditFormData when resetting state
        setEditFormData({} as EditFormData);
    };

    const handleEditFormChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        // Ensure the name corresponds to an editable field before updating state
        if (editableFields.includes(name as keyof ContentItem)) {
           // The name matches a key in EditFormData due to the check above
           setEditFormData(prev => ({ ...prev, [name as keyof EditFormData]: value }));
        }
    };

    // --- Save Handler ---
    const handleSave = async (docId: string) => {
        if (!editingItemId || editingItemId !== docId) return; // Should not happen

        setLoading(true);
        setError(null);

        // Prepare payload for the backend (should match Partial<ContentItem>)
        const payload: Partial<ContentItem> = {};

        // Iterate over editableFields to build the payload from editFormData
        editableFields.forEach(field => {
            // Access value from the EditFormData state, which is guaranteed to be string or undefined
            const formValue = editFormData[field as keyof EditFormData];

            if (field === 'keywords') {
                // Convert comma-separated string back to array for the payload
                if (formValue !== undefined && formValue !== null) { // Check against undefined and null
                   payload.keywords = String(formValue) // Ensure it's treated as string
                       .split(',')
                       .map(k => k.trim())
                       .filter(k => k !== '');
                } else {
                    // If formValue is undefined or null (e.g., field wasn't in form state),
                    // decide how to handle it - maybe an empty array for keywords.
                    payload.keywords = []; // Default empty keywords to empty array
                }
            } else {
                // For other fields, the form value is a string (or undefined/null if not set).
                // Convert empty strings to null if your backend expects null for empty fields.
                if (formValue !== undefined && formValue !== null) {
                     // Assign the string value to the payload.
                     // If the ContentItem type for this field is not string/null/undefined,
                     // you might need type assertions or specific handling here.
                     // Assuming other editable fields are string | null | undefined in ContentItem:
                     payload[field] = (formValue.trim() === '') ? null : formValue as any; // Convert empty string to null
                } else {
                     payload[field] = null as any; // If formValue is undefined/null, set payload field to null
                }
            }
        });

        try {
            const response = await fetch(`${API_URL}/api/update-content/${docId}`, {
                method: "PUT", // Or PATCH if your backend supports it
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(errorData.message || `Update failed with status: ${response.status}`);
            }

            const updatedItem: ContentItem = await response.json(); // Assuming backend returns the updated item

            // Update the item in the searchResults state
            setSearchResults(prevResults =>
                prevResults.map(item => (item._id === docId ? updatedItem : item))
            );

            // Exit edit mode
            handleCancelEdit();

        } catch (err: any) {
            console.error("Update error:", err);
            setError(err.message || "An error occurred while saving.");
            // Keep edit mode active so user can retry or cancel
        } finally {
            setLoading(false);
        }
    };

    // --- Render Helper for Displaying Item Data ---
    const renderItemField = (item: ContentItem, field: keyof ContentItem) => {
        const value = item[field];
        if (field === 'keywords') {
            return (Array.isArray(value) ? value.join(', ') : '');
        }
        if (typeof value === 'object' && value !== null && !(value instanceof Array)) {
             // Handle non-array objects like processing_info
             // Added check for Array instance to not stringify keyword array
            return <pre className="text-xs bg-gray-100 p-1 rounded overflow-auto">{JSON.stringify(value, null, 2)}</pre>;
        }
        // For null, undefined, strings, numbers, booleans, etc.
        return value ?? <span className="text-gray-400 italic">N/A</span>;
    };

    // --- Render Helper for Editable Field ---
    const renderEditableField = (field: keyof ContentItem) => {
         // Access value from the EditFormData state, ensuring it's treated as string for the form
        const value = editFormData[field as keyof EditFormData];
        const isKeywords = field === 'keywords';

        // Use textarea for longer fields like title or potentially summary if added
        const useTextArea = ['title', 'summary'].includes(field); // Add 'summary' if it becomes editable

        // Ensure value is always a string for input elements
        const stringValue = value === undefined || value === null ? '' : String(value);


        if (useTextArea) {
             return (
                 <textarea
                     id={field}
                     name={field} // Name must match keys in EditFormData
                     value={stringValue}
                     onChange={handleEditFormChange}
                     className="w-full border border-gray-300 px-2 py-1 rounded shadow-sm text-sm"
                     rows={2}
                 />
             );
        }

        return (
            <input
                type="text"
                id={field}
                name={field} // Name must match keys in EditFormData
                value={stringValue}
                onChange={handleEditFormChange}
                placeholder={isKeywords ? "Comma-separated keywords" : ""}
                className="w-full border border-gray-300 px-2 py-1 rounded shadow-sm text-sm"
            />
        );
    };


    return (
        <div className="p-4 border rounded shadow-md space-y-4 bg-white">
            <h2 className="text-xl font-semibold text-gray-700 border-b pb-2">Manage Content</h2>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="flex items-end space-x-2">
                <div className="flex-grow">
                    <label htmlFor="searchQuery" className="block text-sm font-medium text-gray-600 mb-1">
                        Search Term
                    </label>
                    <input
                        id="searchQuery"
                        type="search"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full border border-gray-300 px-3 py-2 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        placeholder={`Search by ${searchFields.find(f => f.value === searchField)?.label || '...'}`}
                        disabled={loading}
                    />
                </div>
                <div>
                    <label htmlFor="searchField" className="block text-sm font-medium text-gray-600 mb-1">
                        Search In
                    </label>
                    <select
                        id="searchField"
                        value={searchField}
                        onChange={(e) => setSearchField(e.target.value)}
                        className="border border-gray-300 px-3 py-2 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm h-[42px]" // Match input height
                        disabled={loading}
                    >
                        {searchFields.map((field) => (
                            <option key={field.value} value={field.value}>
                                {field.label}
                            </option>
                        ))}
                    </select>
                </div>
                <button
                    type="submit"
                    disabled={loading || !searchQuery.trim()}
                    className="px-4 py-2 h-[42px] border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    ) : "Search"}
                </button>
            </form>

            {/* Error Display */}
            {error && !loading && (
                <div className="mt-4 p-3 rounded-md text-sm bg-red-100 text-red-700">
                    Error: {error}
                </div>
            )}

            {/* Loading Indicator */}
            {loading && (
                <div className="text-center py-4">
                    <p className="text-gray-500">Loading...</p>
                </div>
            )}


            {/* Search Results */}
            <div className="mt-6 space-y-4">
                {searchResults.map((item) => (
                    <div key={item._id} className="border rounded-lg p-4 shadow space-y-2 bg-gray-50">
                        {editingItemId === item._id ? (
                            // --- Edit Mode ---
                            <>
                                <h3 className="text-lg font-semibold text-gray-800 mb-2">Editing: {item.job_id}</h3>
                                {editableFields.map(field => (
                                    <div key={field} className="grid grid-cols-4 gap-2 items-center">
                                        <label htmlFor={field} className="text-sm font-medium text-gray-600 col-span-1 text-right pr-2">
                                            {field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ')}:
                                        </label>
                                        <div className="col-span-3">
                                            {renderEditableField(field)}
                                        </div>
                                    </div>
                                ))}
                                {error && editingItemId === item._id && (
                                    <div className="mt-2 p-2 rounded-md text-sm bg-red-100 text-red-700 col-span-4">
                                        Save Error: {error}
                                    </div>
                                )}
                                <div className="flex justify-end space-x-2 pt-3">
                                    <button
                                        onClick={handleCancelEdit}
                                        className="px-3 py-1 rounded border border-gray-300 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                        disabled={loading}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => handleSave(item._id)}
                                        className="px-3 py-1 rounded bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
                                        disabled={loading}
                                    >
                                        {loading ? "Saving..." : "Save Changes"}
                                    </button>
                                </div>
                            </>
                        ) : (
                            // --- Display Mode ---
                            <>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-800">{item.title || <span className="italic text-gray-500">No Title</span>}</h3>
                                        <p className="text-xs text-gray-500">Job ID: {item.job_id} | DB ID: {item._id}</p>
                                    </div>
                                    <button
                                        onClick={() => handleEditClick(item)}
                                        className="px-3 py-1 rounded border border-gray-300 text-sm text-gray-700 hover:bg-gray-100"
                                    >
                                        Edit
                                    </button>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                    <div><strong>Source:</strong> <span className="break-all">{renderItemField(item, 'source_location')} ({item.source_type})</span></div>
                                    {item.url && <div><strong>URL:</strong> <span className="break-all">{renderItemField(item, 'url')}</span></div>}
                                    <div><strong>Speaker:</strong> {renderItemField(item, 'speaker')}</div>
                                    <div><strong>Location:</strong> {renderItemField(item, 'location')}</div>
                                    <div><strong>Category:</strong> {renderItemField(item, 'category')}</div>
                                    <div><strong>Language:</strong> {renderItemField(item, 'detected_language')}</div>
                                    <div className="col-span-2"><strong>Keywords:</strong> {renderItemField(item, 'keywords')}</div>
                                    <div><strong>Added:</strong> {item.date_added ? new Date(item.date_added).toLocaleString() : 'N/A'}</div>
                                    <div><strong>Updated:</strong> {item.last_updated ? new Date(item.last_updated).toLocaleString() : 'N/A'}</div>
                                </div>
                            </>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ManageContentCard;