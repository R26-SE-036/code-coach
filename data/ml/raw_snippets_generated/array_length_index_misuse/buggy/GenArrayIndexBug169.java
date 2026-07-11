public class GenArrayIndexBug169 {
    static void showLast(int[] prices) {
        System.out.println(prices[prices.length]);
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
