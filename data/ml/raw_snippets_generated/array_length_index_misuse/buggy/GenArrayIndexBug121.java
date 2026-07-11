public class GenArrayIndexBug121 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void showLast(int[] stocks) {
        System.out.println(stocks[stocks.length]);
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
