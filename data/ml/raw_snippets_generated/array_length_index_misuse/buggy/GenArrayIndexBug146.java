public class GenArrayIndexBug146 {
    static void stampLast(int[] values, int value) {
        values[values.length] = value;
    }
}
