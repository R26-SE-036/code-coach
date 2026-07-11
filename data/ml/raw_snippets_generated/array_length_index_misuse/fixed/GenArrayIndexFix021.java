public class GenArrayIndexFix021 {
    static void showLast(int[] totals) {
        System.out.println(totals[totals.length - 1]);
    }

    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }
}
