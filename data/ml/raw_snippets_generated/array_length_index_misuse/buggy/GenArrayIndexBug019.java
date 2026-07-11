public class GenArrayIndexBug019 {
    static void stampLast(int[] values, int value) {
        values[values.length] = value;
    }
}
