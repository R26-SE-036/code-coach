public class GenArrayIndexBug166 {
    static boolean isEven1(int limit) {
        return limit % 2 == 0;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }

    static void stampLast(int[] totals, int value) {
        totals[totals.length] = value;
    }
}
