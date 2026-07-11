public class GenOffByOneFix098 {
    static int[] duplicate(int[] ages) {
        int[] copy = new int[ages.length];
        for (int i = 0; i < ages.length; i++) {
            copy[i] = ages[i];
        }
        return copy;
    }
}
