public class GenArrayIndexFix107 {
    static int lastOf(int[] ages) {
        return ages[ages.length - 1];
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain2(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static int sum3(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll5(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
