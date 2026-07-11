public class GenArrayIndexBug170 {
    static void stampLast(int[] totals, int value) {
        totals[totals.length] = value;
    }
}
