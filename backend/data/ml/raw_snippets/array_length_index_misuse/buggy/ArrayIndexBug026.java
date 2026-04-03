public class ArrayIndexBug026 {
    public int bumpLast(int[] totals) {
        totals[totals.length] = totals[0] + 1;
        return totals[0];
    }
}