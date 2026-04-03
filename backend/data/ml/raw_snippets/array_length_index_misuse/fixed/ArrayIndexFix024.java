public class ArrayIndexFix024 {
    public int getTrimmedLast(int[] values) {
        int picked = values[values.length - 1];
        return picked - 1;
    }
}