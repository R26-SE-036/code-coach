public class GenArrayIndexBug087 {
    static void stampLast(int[] totals, int value) {
        totals[totals.length] = value;
    }
}
