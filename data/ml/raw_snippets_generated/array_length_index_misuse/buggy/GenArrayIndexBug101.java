public class GenArrayIndexBug101 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length] = value;
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }

    static String describe3(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
