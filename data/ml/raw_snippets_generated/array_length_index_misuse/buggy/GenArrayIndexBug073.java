public class GenArrayIndexBug073 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain2(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int lastOf(int[] stocks) {
        return stocks[stocks.length];
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int largest4(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }
}
