export const getFileIcon = (fileType?: string) => {
  if (!fileType) return "📁";
  const type = fileType.split("/")[0];
  const subtype = fileType.split("/")[1];

  switch (type) {
    case "image":
      return "🖼️";
    case "application":
      switch (subtype) {
        case "pdf":
          return "📄";
        case "vnd.openxmlformats-officedocument.wordprocessingml.document":
          return "📝";
        case "vnd.ms-powerpoint":
        case "vnd.openxmlformats-officedocument.presentationml.presentation":
          return "📊";
        case "vnd.ms-excel":
        case "vnd.openxmlformats-officedocument.spreadsheetml.sheet":
          return "📈";
        default:
          return "📁";
      }
    default:
      return "📁";
  }
};

export const getFileExtension = (filename: string) => {
  return filename.split(".").pop()?.toLowerCase() || "";
};
