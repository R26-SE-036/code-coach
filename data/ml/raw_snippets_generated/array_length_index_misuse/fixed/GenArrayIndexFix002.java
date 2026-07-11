public class GenArrayIndexFix002 {
    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }
}
