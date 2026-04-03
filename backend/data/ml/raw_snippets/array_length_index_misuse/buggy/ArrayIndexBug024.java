public class ArrayIndexBug024 {
    public int getTrimmedLast(int[] values) {
        int picked = values[values.length];
        return picked - 1;
    }
}