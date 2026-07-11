public class GenArrayIndexBug054 {
    static void stampLast(int[] sizes, int value) {
        sizes[sizes.length] = value;
    }
}
