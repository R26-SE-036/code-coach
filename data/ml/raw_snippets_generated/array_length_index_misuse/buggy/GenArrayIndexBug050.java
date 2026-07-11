public class GenArrayIndexBug050 {
    static void stampLast(int[] totals, int value) {
        totals[totals.length] = value;
    }
}
