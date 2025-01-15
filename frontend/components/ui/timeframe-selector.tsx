"use client";

import React, { useState,} from 'react';
import { 
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface TimeframeSelectorProps {
  onTimeframeChange: (hours: string) => void;
  defaultValue?: string;
  defaultUnit?: 'hours' | 'days';
}

const TimeframeSelector: React.FC<TimeframeSelectorProps> = ({ 
  onTimeframeChange,
  defaultValue = '24',
  defaultUnit = 'hours'
}) => {
  const [timeUnit, setTimeUnit] = useState<'hours' | 'days'>(defaultUnit);
  const [timeValue, setTimeValue] = useState<string>(defaultValue);
  const [inputValue, setInputValue] = useState<string>(defaultValue);

  const calculateHours = (value: string, unit: 'hours' | 'days'): number => {
    const numValue = parseInt(value) || 0;
    return unit === 'days' ? numValue * 24 : numValue;
  };

  const handleSearch = () => {
    const hours = calculateHours(timeValue, timeUnit);
    if (hours > 0) {
      onTimeframeChange(hours.toString());
    }
  };

  const handleTimeValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === '' || /^\d+$/.test(value)) {
      setInputValue(value);
      setTimeValue(value);
    }
  };

  const handleUnitChange = (value: 'hours' | 'days') => {
    setTimeUnit(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <Input
        type="number"
        min="1"
        value={inputValue}
        onChange={handleTimeValueChange}
        onKeyDown={handleKeyDown}
        className="w-20"
        placeholder="Time"
      />
      <Select value={timeUnit} onValueChange={handleUnitChange}>
        <SelectTrigger className="w-24">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="hours">Hours</SelectItem>
            <SelectItem value="days">Days</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <Button 
        onClick={handleSearch}
        size="icon"
        variant="ghost"
      >
        <Search className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default TimeframeSelector;