public class ArrayIndexBug013 {
    public int getLastSize(int[] sizes) {
        return sizes[sizes.length] * 2;
    }
}