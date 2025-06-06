import React, { useState, useMemo } from 'react';
import { ROIReportData } from '../../types/roi-workflow';

interface ResultsTableProps {
  data: ROIReportData[];
  onDataChange: (updatedData: ROIReportData[]) => void;
  className?: string;
  isEditable?: boolean;
}

type SortField = keyof ROIReportData;
type SortDirection = 'asc' | 'desc';

const PRIORITY_COLORS = {
  high: 'text-red-400 bg-red-400/10 border-red-400/30',
  medium: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
  low: 'text-green-400 bg-green-400/10 border-green-400/30'
};

const CONTACT_TYPE_COLORS = {
  prospective: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  existing: 'text-purple-400 bg-purple-400/10 border-purple-400/30'
};

export function ResultsTable({ 
  data, 
  onDataChange, 
  className = '', 
  isEditable = true 
}: ResultsTableProps) {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [editingCell, setEditingCell] = useState<{ id: string; field: keyof ROIReportData } | null>(null);
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [filterContactType, setFilterContactType] = useState<string>('all');

  const filteredAndSortedData = useMemo(() => {
    let filtered = data;

    // Apply filters
    if (filterPriority !== 'all') {
      filtered = filtered.filter(item => item.priorityLevel === filterPriority);
    }
    if (filterContactType !== 'all') {
      filtered = filtered.filter(item => item.contactType === filterContactType);
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortDirection === 'asc' ? comparison : -comparison;
      }
      
      if (Array.isArray(aValue) && Array.isArray(bValue)) {
        const aStr = aValue.join(', ');
        const bStr = bValue.join(', ');
        const comparison = aStr.localeCompare(bStr);
        return sortDirection === 'asc' ? comparison : -comparison;
      }
      
      return 0;
    });
  }, [data, sortField, sortDirection, filterPriority, filterContactType]);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleCellEdit = (id: string, field: keyof ROIReportData, value: string) => {
    if (!isEditable) return;

    const updatedData = data.map(item => {
      if (item.id === id) {
        if (field === 'actionItems') {
          return { ...item, [field]: value.split(',').map(s => s.trim()) };
        }
        return { ...item, [field]: value };
      }
      return item;
    });
    
    onDataChange(updatedData);
    setEditingCell(null);
  };

  const getSortIcon = (field: SortField) => {
    if (field !== sortField) return '↕️';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  if (data.length === 0) {
    return (
      <div className="text-center py-12 border border-terminal-cyan/30 rounded-lg">
        <div className="text-4xl mb-4">📊</div>
        <h3 className="text-lg font-terminal text-terminal-cyan mb-2">No Data Available</h3>
        <p className="text-terminal-cyan/70">Upload and process an audio recording to see ROI data here.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header and Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h3 className="text-xl font-terminal text-terminal-cyan mb-1">ROI Report Results</h3>
          <p className="text-terminal-cyan/70 text-sm">
            {filteredAndSortedData.length} of {data.length} records
            {isEditable && ' • Click any cell to edit'}
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-terminal-cyan/70 text-sm">Priority:</label>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="bg-terminal-bg border border-terminal-cyan/30 text-terminal-cyan text-sm px-2 py-1 rounded"
            >
              <option value="all">All</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-terminal-cyan/70 text-sm">Contact:</label>
            <select
              value={filterContactType}
              onChange={(e) => setFilterContactType(e.target.value)}
              className="bg-terminal-bg border border-terminal-cyan/30 text-terminal-cyan text-sm px-2 py-1 rounded"
            >
              <option value="all">All</option>
              <option value="prospective">Prospective</option>
              <option value="existing">Existing</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-terminal-cyan/30 rounded-lg shadow-lg">
        <table className="w-full min-w-[800px]">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-terminal-cyan/30 bg-terminal-cyan/5 backdrop-blur-sm">
              {[
                { key: 'name', label: 'Name' },
                { key: 'company', label: 'Company' },
                { key: 'position', label: 'Position' },
                { key: 'discussion', label: 'Discussion' },
                { key: 'contactType', label: 'Contact Type' },
                { key: 'priorityLevel', label: 'Priority' },
                { key: 'actionItems', label: 'Action Items' }
              ].map(({ key, label }) => (
                <th
                  key={key}
                  className="px-6 py-4 text-left font-terminal text-terminal-cyan cursor-pointer hover:bg-terminal-cyan/10 transition-all duration-200 hover:shadow-md first:rounded-tl-lg last:rounded-tr-lg"
                  onClick={() => handleSort(key as SortField)}
                >
                  <div className="flex items-center gap-2">
                    <span>{label}</span>
                    <span className="text-xs transition-transform duration-200 hover:scale-110">{getSortIcon(key as SortField)}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedData.map((item, index) => (
              <tr
                key={item.id}
                className={`
                  border-b border-terminal-cyan/20 hover:bg-blue-50/10 hover:shadow-md transition-all duration-200 hover:scale-[1.01] group
                  ${index % 2 === 0 ? 'bg-terminal-bg' : 'bg-gray-50/5'}
                `}
              >
                <td className="px-6 py-4">
                  <EditableCell
                    value={item.name}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'name'}
                    onEdit={(value) => handleCellEdit(item.id, 'name', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'name' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                  />
                </td>
                <td className="px-6 py-4">
                  <EditableCell
                    value={item.company}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'company'}
                    onEdit={(value) => handleCellEdit(item.id, 'company', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'company' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                  />
                </td>
                <td className="px-6 py-4">
                  <EditableCell
                    value={item.position}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'position'}
                    onEdit={(value) => handleCellEdit(item.id, 'position', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'position' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                  />
                </td>
                <td className="px-6 py-4 max-w-xs">
                  <EditableCell
                    value={item.discussion}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'discussion'}
                    onEdit={(value) => handleCellEdit(item.id, 'discussion', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'discussion' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                    multiline
                  />
                </td>
                <td className="px-6 py-4">
                  <EditableSelectCell
                    value={item.contactType}
                    options={[
                      { value: 'prospective', label: 'Prospective' },
                      { value: 'existing', label: 'Existing' }
                    ]}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'contactType'}
                    onEdit={(value) => handleCellEdit(item.id, 'contactType', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'contactType' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                    colorClass={CONTACT_TYPE_COLORS[item.contactType] || 'text-gray-400 bg-gray-400/10 border-gray-400/30'}
                    allowCustom={true}
                    customPlaceholder="Enter custom contact type"
                  />
                </td>
                <td className="px-6 py-4">
                  <EditableSelectCell
                    value={item.priorityLevel}
                    options={[
                      { value: 'high', label: 'High' },
                      { value: 'medium', label: 'Medium' },
                      { value: 'low', label: 'Low' }
                    ]}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'priorityLevel'}
                    onEdit={(value) => handleCellEdit(item.id, 'priorityLevel', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'priorityLevel' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                    colorClass={PRIORITY_COLORS[item.priorityLevel] || 'text-gray-400 bg-gray-400/10 border-gray-400/30'}
                    allowCustom={true}
                    customPlaceholder="Enter custom priority level"
                  />
                </td>
                <td className="px-6 py-4 max-w-xs">
                  <EditableCell
                    value={item.actionItems.join(', ')}
                    isEditing={editingCell?.id === item.id && editingCell?.field === 'actionItems'}
                    onEdit={(value) => handleCellEdit(item.id, 'actionItems', value)}
                    onStartEdit={() => setEditingCell({ id: item.id, field: 'actionItems' })}
                    onCancelEdit={() => setEditingCell(null)}
                    isEditable={isEditable}
                    multiline
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-terminal-cyan/30">
        <div className="text-center p-4 border border-terminal-cyan/30 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 bg-terminal-cyan/5">
          <div className="text-2xl font-terminal text-terminal-cyan">{data.length}</div>
          <div className="text-sm text-terminal-cyan/70">Total Contacts</div>
        </div>
        <div className="text-center p-4 border border-red-400/30 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 bg-red-400/5">
          <div className="text-2xl font-terminal text-red-400">
            {data.filter(item => item.priorityLevel === 'high').length}
          </div>
          <div className="text-sm text-red-400/70">High Priority</div>
        </div>
        <div className="text-center p-4 border border-blue-400/30 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 bg-blue-400/5">
          <div className="text-2xl font-terminal text-blue-400">
            {data.filter(item => item.contactType === 'prospective').length}
          </div>
          <div className="text-sm text-blue-400/70">Prospective Clients</div>
        </div>
      </div>
    </div>
  );
}

// Editable Cell Component
interface EditableCellProps {
  value: string;
  isEditing: boolean;
  onEdit: (value: string) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  isEditable: boolean;
  multiline?: boolean;
}

function EditableCell({
  value,
  isEditing,
  onEdit,
  onStartEdit,
  onCancelEdit,
  isEditable,
  multiline = false
}: EditableCellProps) {
  const [editValue, setEditValue] = useState(value);

  React.useEffect(() => {
    setEditValue(value);
  }, [value]);

  const handleSave = () => {
    onEdit(editValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !multiline) {
      handleSave();
    } else if (e.key === 'Escape') {
      setEditValue(value);
      onCancelEdit();
    }
  };

  if (isEditing && isEditable) {
    return (
      <div className="space-y-2">
        {multiline ? (
          <textarea
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-terminal-bg border border-terminal-cyan text-terminal-cyan text-sm p-2 rounded-lg transition-all duration-200 focus:ring-2 focus:ring-terminal-cyan/50 focus:border-terminal-cyan"
            rows={3}
            autoFocus
          />
        ) : (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-terminal-bg border border-terminal-cyan text-terminal-cyan text-sm p-2 rounded-lg transition-all duration-200 focus:ring-2 focus:ring-terminal-cyan/50 focus:border-terminal-cyan"
            autoFocus
          />
        )}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="text-xs bg-terminal-cyan text-black px-3 py-1 rounded-lg hover:bg-terminal-cyan/80 transition-all duration-200 hover:scale-105 hover:shadow-md font-medium"
          >
            Save
          </button>
          <button
            onClick={onCancelEdit}
            className="text-xs border border-terminal-cyan/50 text-terminal-cyan px-3 py-1 rounded-lg hover:bg-terminal-cyan hover:text-black transition-all duration-200 hover:scale-105 hover:shadow-md"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        text-terminal-cyan text-sm break-words transition-all duration-200
        ${isEditable ? 'cursor-pointer hover:bg-terminal-cyan/10 p-2 rounded-lg hover:scale-105 hover:shadow-md group-hover:bg-terminal-cyan/5' : ''}
      `}
      onClick={isEditable ? onStartEdit : undefined}
      title={isEditable ? 'Click to edit' : undefined}
    >
      {value || <span className="text-terminal-cyan/50 italic">Empty</span>}
    </div>
  );
}

// Editable Select Cell Component
interface EditableSelectCellProps {
  value: string;
  options: { value: string; label: string }[];
  isEditing: boolean;
  onEdit: (value: string) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  isEditable: boolean;
  colorClass?: string;
  allowCustom?: boolean;
  customPlaceholder?: string;
}

function EditableSelectCell({
  value,
  options,
  isEditing,
  onEdit,
  onStartEdit,
  onCancelEdit,
  isEditable,
  colorClass = '',
  allowCustom = false,
  customPlaceholder = 'Enter custom value'
}: EditableSelectCellProps) {
  const [editValue, setEditValue] = useState(value);
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [customValue, setCustomValue] = useState('');

  React.useEffect(() => {
    setEditValue(value);
    // Check if current value is not in predefined options
    const isValueInOptions = options.some(opt => opt.value === value);
    if (allowCustom && !isValueInOptions && value) {
      setIsCustomMode(true);
      setCustomValue(value);
    } else {
      setIsCustomMode(false);
      setCustomValue('');
    }
  }, [value, options, allowCustom]);

  const handleSave = () => {
    const finalValue = isCustomMode ? customValue : editValue;
    onEdit(finalValue);
    setIsCustomMode(false);
    setCustomValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      setEditValue(value);
      setIsCustomMode(false);
      setCustomValue('');
      onCancelEdit();
    }
  };

  const handleSelectChange = (selectedValue: string) => {
    if (selectedValue === '__custom__') {
      setIsCustomMode(true);
      setCustomValue('');
    } else {
      setIsCustomMode(false);
      setEditValue(selectedValue);
    }
  };

  if (isEditing && isEditable) {
    return (
      <div className="space-y-2">
        {!isCustomMode ? (
          <select
            value={editValue}
            onChange={(e) => handleSelectChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-terminal-bg border border-terminal-cyan text-terminal-cyan text-sm p-1 rounded"
            autoFocus
          >
            {options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
            {allowCustom && (
              <option value="__custom__">+ Add custom...</option>
            )}
          </select>
        ) : (
          <div className="space-y-2">
            <input
              type="text"
              value={customValue}
              onChange={(e) => setCustomValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={customPlaceholder}
              className="w-full bg-terminal-bg border border-terminal-cyan text-terminal-cyan text-sm p-1 rounded"
              autoFocus
            />
            <button
              onClick={() => {
                setIsCustomMode(false);
                setCustomValue('');
              }}
              className="text-xs text-terminal-cyan/70 hover:text-terminal-cyan"
            >
              ← Back to preset options
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={isCustomMode && !customValue.trim()}
            className="text-xs bg-terminal-cyan text-black px-2 py-1 rounded hover:bg-terminal-cyan/80 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save
          </button>
          <button
            onClick={() => {
              setEditValue(value);
              setIsCustomMode(false);
              setCustomValue('');
              onCancelEdit();
            }}
            className="text-xs border border-terminal-cyan/50 text-terminal-cyan px-2 py-1 rounded hover:bg-terminal-cyan hover:text-black"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  const displayValue = options.find(opt => opt.value === value)?.label || value;

  return (
    <div
      className={`
        ${isEditable ? 'cursor-pointer hover:bg-terminal-cyan/10' : ''}
      `}
      onClick={isEditable ? onStartEdit : undefined}
      title={isEditable ? 'Click to edit' : undefined}
    >
      <span className={`inline-block px-2 py-1 text-xs rounded border ${colorClass}`}>
        {displayValue}
      </span>
    </div>
  );
} 