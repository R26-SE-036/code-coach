public class GenArrayIndexFix156 {
    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static void stampLast(int[] weights, int value) {
        weights[weights.length - 1] = value;
    }
}
