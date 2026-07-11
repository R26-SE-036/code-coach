public class GenOffByOneBug087 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int[] duplicate(int[] stocks) {
        int[] copy = new int[stocks.length];
        for (int i = 0; i <= stocks.length; i++) {
            copy[i] = stocks[i];
        }
        return copy;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll3(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int drain5(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }
}
