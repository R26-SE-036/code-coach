public class GenArrayIndexBug144 {
    static void stampLast(int[] totals, int value) {
        totals[totals.length] = value;
    }
}
