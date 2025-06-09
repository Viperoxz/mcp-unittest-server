/**
 * Example JavaScript module for testing the MCP Unit Test Generator
 */

class ArrayUtils {
    /**
     * Check if array is empty
     */
    static isEmpty(arr) {
        return !arr || arr.length === 0;
    }
    
    /**
     * Get unique elements from array
     */
    static unique(arr) {
        if (this.isEmpty(arr)) {
            return [];
        }
        return [...new Set(arr)];
    }
    
    /**
     * Flatten nested array
     */
    static flatten(arr) {
        if (this.isEmpty(arr)) {
            return [];
        }
        return arr.reduce((flat, item) => {
            return flat.concat(Array.isArray(item) ? this.flatten(item) : item);
        }, []);
    }
    
    /**
     * Chunk array into smaller arrays
     */
    static chunk(arr, size) {
        if (this.isEmpty(arr) || size <= 0) {
            return [];
        }
        
        const chunks = [];
        for (let i = 0; i < arr.length; i += size) {
            chunks.push(arr.slice(i, i + size));
        }
        return chunks;
    }
    
    /**
     * Find intersection of two arrays
     */
    static intersection(arr1, arr2) {
        if (this.isEmpty(arr1) || this.isEmpty(arr2)) {
            return [];
        }
        return arr1.filter(item => arr2.includes(item));
    }
    
    /**
     * Find difference between two arrays
     */
    static difference(arr1, arr2) {
        if (this.isEmpty(arr1)) {
            return [];
        }
        if (this.isEmpty(arr2)) {
            return [...arr1];
        }
        return arr1.filter(item => !arr2.includes(item));
    }
}

/**
 * Utility functions for numbers
 */
function isEven(num) {
    return typeof num === 'number' && num % 2 === 0;
}

function isOdd(num) {
    return typeof num === 'number' && num % 2 !== 0;
}

function clamp(num, min, max) {
    return Math.min(Math.max(num, min), max);
}

function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
}

module.exports = {
    ArrayUtils,
    isEven,
    isOdd,
    clamp,
    randomBetween
};

