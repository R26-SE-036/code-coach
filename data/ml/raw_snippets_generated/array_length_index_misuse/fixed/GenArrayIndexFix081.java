public class GenArrayIndexFix081 {
    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static void stampLast(int[] totals, int value) {
        totals[totals.length - 1] = value;
    }
}
