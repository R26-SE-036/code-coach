public class ArrayIndexBug018 {
    public void updateLast(int[] values) {
        values[values.length] = 99;
    }
}