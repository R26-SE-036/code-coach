public class GenArrayIndexFix048 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
