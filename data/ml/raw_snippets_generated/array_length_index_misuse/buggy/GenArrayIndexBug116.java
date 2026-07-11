public class GenArrayIndexBug116 {
    static void stampLast(int[] weights, int value) {
        weights[weights.length] = value;
    }

    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }
}
