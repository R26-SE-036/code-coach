public class GenArrayIndexBug106 {
    static void showLast(int[] totals) {
        System.out.println(totals[totals.length]);
    }

    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }
}
