public class GenArrayIndexFix116 {
    static void stampLast(int[] weights, int value) {
        weights[weights.length - 1] = value;
    }

    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }
}
