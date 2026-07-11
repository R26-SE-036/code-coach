public class GenArrayIndexBug021 {
    static void showLast(int[] totals) {
        System.out.println(totals[totals.length]);
    }

    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }
}
