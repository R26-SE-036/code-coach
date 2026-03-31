public class OffByOneBug009 {
    public static void main(String[] args) {
        int[] source = { 2, 4, 6, 8 };
        int[] target = new int[source.length];

        for (int i = 0; i <= source.length; i++) {
            target[i] = source[i];
        }
    }
}