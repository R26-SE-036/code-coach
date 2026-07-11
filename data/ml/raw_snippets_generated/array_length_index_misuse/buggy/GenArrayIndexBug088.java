public class GenArrayIndexBug088 {
    static void stampLast(int[] values, int value) {
        values[values.length] = value;
    }
}
