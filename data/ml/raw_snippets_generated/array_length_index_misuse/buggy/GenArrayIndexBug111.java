public class GenArrayIndexBug111 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length];
    }
}
